# Load Food Base LA layers in R.
#
#   source("load_layer.R")
#   catalog()                       # list of all 245 layers
#   x <- load_layer("Retail_Food_Outlets_Restaurants_Restaurants_2026_March")
#
# Needs: install.packages(c("arrow", "sf"))

data_dir <- "data"

# Table of all layers (name, group, title, number of features, files)
catalog <- function() {
  read.csv(file.path(data_dir, "catalog.csv"))
}

# Return one layer as an sf object (EPSG:4326)
load_layer <- function(layer) {
  info <- catalog()
  info <- info[info$layer == layer, ]
  if (nrow(info) != 1) stop("Unknown layer: ", layer, ". See catalog()$layer")

  attrs  <- as.data.frame(arrow::read_parquet(file.path(data_dir, "attributes", info$attributes_file)))
  shapes <- arrow::read_parquet(file.path(data_dir, "geometries", info$geometry_file))

  # 64-bit integer columns (e.g., tract IDs) as regular numbers
  is64 <- vapply(attrs, inherits, logical(1), "integer64")
  attrs[is64] <- lapply(attrs[is64], as.numeric)

  # Shapes are stored as WKB; convert them to sf geometries
  geom <- sf::st_as_sfc(structure(as.list(shapes$geometry), class = "WKB"), crs = 4326)

  # Match each row to its shape (rows without a shape get an empty geometry)
  geometry <- geom[match(attrs$geom_id, shapes$geom_id)]

  # Layers mixing e.g. POLYGON and MULTIPOLYGON become all MULTIPOLYGON (as sf::read_sf does)
  types <- unique(sub("^MULTI", "", as.character(sf::st_geometry_type(geometry))))
  if (inherits(geometry, "sfc_GEOMETRY") && length(types) == 1)
    geometry <- sf::st_cast(geometry, paste0("MULTI", types))

  attrs$geom_id <- NULL
  sf::st_sf(attrs, geometry = geometry)
}

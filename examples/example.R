# Minimal example: load and map Food Base LA layers in R.
# Run from the repository root:  Rscript examples/example.R
# Needs: install.packages(c("arrow", "sf"))

source("load_layer.R")

# 1. See which layers are available
layers <- catalog()
head(layers[, c("layer", "title", "n_features")])

# 2. Load one layer as an sf object
tracts <- load_layer("Resident_Health_Food_Insecurity_Food_Insecurity_2022")
restaurants <- load_layer("Retail_Food_Outlets_Restaurants_Restaurants_2026_March")

# 3. Use it like any other sf object
names(tracts)
nrow(restaurants)

plot(sf::st_geometry(tracts), border = "grey80", main = "Restaurants, March 2026")
plot(sf::st_geometry(restaurants), pch = ".", col = "firebrick", add = TRUE)

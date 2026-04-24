library(shiny)
library(visNetwork)
library(dplyr)
library(scales)
library(igraph)
library(shinymanager)
library(tidyr)
library(readr)
library(purrr)

# PATHS
data_dir <- "/work/YOU-DARE/controversy-mapping/data/work"

# READ DATA - remember to un-comment!
df <- read_csv(file.path(data_dir, "SE_annotated_labels_flat.csv"))
#df <- read_csv(file.path(data_dir, "RO_annotated_labels_flat.csv"))

# Colours
type_colours = c(
  "actor" = "#b19335",
  "label" = "#cc445b"
)

# Nodes
nodes <- df |> 
  select(id = source) |>
  mutate(type = "actor") |> 
  bind_rows(select(df, id = label) |> 
              mutate(type = "label")) |>
  distinct() |>
  mutate(label = id)

# Edges
edges <- df |>
  select(source, label) |> 
  mutate(
    from = source,
    to = label,
    id = paste0("edge_", row_number())
  ) |>
  select(id, from, to) |> 
  distinct(from, to, .keep_all = TRUE)

# page setup
ui <- fluidPage(
  title = "Stable Layout Network",
  fillPage(
    sidebarLayout(
      sidebarPanel(
        #checkboxGroupInput("filterNodes", "Select nodes:", choices = unique(nodes$id), selected = unique(nodes$id)),
        
        width = 3
      ),
      mainPanel(
        visNetworkOutput("network_proxy_update", width = "100%", height = "90vh"),
        width = 9
      )
    )
  )
)

# server
server <- function(input, output, session) {
  
  # call the server part
  # check_credentials returns a function to authenticate users
  res_auth <- secure_server(
    check_credentials = check_credentials(credentials)
  )
  
  output$auth_output <- renderPrint({
    reactiveValuesToList(res_auth)
  })
  
  filtered_nodes <- reactive({
    nodes
  })
  
  
  filtered_nodes <- reactive({
    edge_data <- filtered_edges()
    
    if (nrow(edge_data) == 0) {
      # No edges — show all available nodes
      base_nodes <- nodes
    } else {
      node_ids <- unique(c(edge_data$from, edge_data$to))
      base_nodes <- nodes |> filter(id %in% node_ids)
    }
    
    base_nodes
  })
  
  filtered_edges <- reactive({
  
    edge_set <- edges
    
    edge_set
  })
  
  output$network_proxy_update <- renderVisNetwork({
    node_data <- filtered_nodes()
    edge_data <- filtered_edges()
    arrow_type <- "to"
  
    
    node_data$color.background <- type_colours[node_data$type]
    
    vis <- visNetwork(node_data, edge_data) |>
      visNodes(color = list(border = "black"),
               size = 10) |>
      visEdges(arrows = arrow_type,
               width = 0.8) |>
      visOptions(
        highlightNearest = TRUE,
        nodesIdSelection = FALSE
      ) |>
      visPhysics(
        solver = "repulsion",
        repulsion = list(
          nodeDistance = 250,   # Increase spacing between nodes
          springLength = 200    # (Optional) controls natural spring-like spacing
        ),
        stabilization = list(
          enabled = TRUE,
          iterations = 1000
        ),
        enabled = FALSE
      ) |>
      visLayout(randomSeed = 1234)
    
    
    vis
    
    
  })
  
}

shinyApp(ui, server)
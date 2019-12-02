resource "mongodbatlas_project" "velkoz" {
    name = var.application_name
    org_id = var.atlas_org_id
}

# resource "mongodbatlas_cluster" "user" {
#     project_id = mongodbatlas_project.velkoz.id
#     name = "user"
#     num_shards = 1

#     replication_factor = 0
#     backup_enabled = false
#     auto_scaling_disk_gb_enabled = false
#     mongo_db_major_version = "4.0"

#     provider_name = "AWS"
#     provider_instance_size_name = "M2"
#     provider_region_name = "US_EAST_1" 
# }

resource "mongodbatlas_project" "velkoz" {
  name   = "velkoz"
  org_id = var.atlas_org_id
}

resource "mongodbatlas_database_user" "user" {
  username           = var.mongo_user
  password           = var.mongo_password
  project_id         = mongodbatlas_project.velkoz.id
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = "velkoz"
  }
}

#####
#### Sadly, the TF provider does not support creation of M0 clusters. In the vein of keeping costs down to a minimum, I created the cluster manually
#####
# resource "mongodbatlas_cluster" "cluster-test" {
#   project_id   = mongodbatlas_project.velkoz.id
#   name         = "velkoz"
#   num_shards   = 1

#   replication_factor           = 3
#   provider_backup_enabled      = true
#   auto_scaling_disk_gb_enabled = true
#   mongo_db_major_version       = "4.0"

#   //Provider Settings "block"
#   provider_name               = "AWS"
#   disk_size_gb                = 100
#   provider_disk_iops          = 300
#   provider_volume_type        = "STANDARD"
#   provider_encrypt_ebs_volume = true
#   provider_instance_size_name = "M10"
#   provider_region_name        = "US_EAST_1"
# }
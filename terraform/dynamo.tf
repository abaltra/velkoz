resource "aws_dynamodb_table" "player_update_roll" {
    name = "UpdateRoll"
    billing_mode = "PAY_PER_REQUEST"
    stream_enabled = true
    stream_view_type = "NEW_AND_OLD_IMAGES"

    hash_key = "AccountId"
    range_key = "LastUpdate"

    attribute {
        name = "AccountId"
        type = "S"
    }

    attribute {
        name = "LastUpdate"
        type = "S"
    }

    ttl {
        attribute_name = "NextUpdate"
        enabled = true
    }
}
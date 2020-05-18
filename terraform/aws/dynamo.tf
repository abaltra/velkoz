resource "aws_dynamodb_table" "lol_player_update_roll" {
    name = "LolUpdateRoll"
    billing_mode = "PAY_PER_REQUEST"
    stream_enabled = true
    stream_view_type = "OLD_IMAGE"

    hash_key = "UserId"
    range_key = "LastUpdate"

    attribute {
        name = "UserId"
        type = "S"
    }

    attribute {
        name = "LastUpdate"
        type = "S"
    }

    ttl {
        attribute_name = "NextUpdateRoll"
        enabled = true
    }
}
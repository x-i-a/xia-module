locals {
  source_config = yamldecode(file(var.source_file))
}

resource "local_file" "example" {
  for_each = local.source_config

  content  = "Module of resource created!"
  filename = "${each.key}.txt"
}
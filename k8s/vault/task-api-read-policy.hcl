path "secret/data/task-api/config" {
  capabilities = ["read"]
}

path "secret/data/task-service/db" {
  capabilities = ["read"]
}

path "secret/data/task-service/redis" {
  capabilities = ["read"]
}

path "secret/data/kibana/encryption-keys" {
  capabilities = ["read"]
}

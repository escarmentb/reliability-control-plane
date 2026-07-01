variable "kubeconfig_path" {
  type        = string
  description = "Path to the kubeconfig used by the Kubernetes provider."
  default     = "~/.kube/config"
}

variable "namespace" {
  type        = string
  description = "Namespace for Reliability Lab resources."
  default     = "reliability-lab"
}


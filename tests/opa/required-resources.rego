package k8srequiredresources

containers := array.concat(
  object.get(input.review.object.spec, "containers", []),
  object.get(input.review.object.spec, "initContainers", [])
)

violation contains {"msg": msg} if {
  container := containers[_]
  resources := object.get(container, "resources", {})
  requests := object.get(resources, "requests", {})
  not object.get(requests, "cpu", false)
  msg := sprintf("Container %q must define a CPU request", [container.name])
}

violation contains {"msg": msg} if {
  container := containers[_]
  resources := object.get(container, "resources", {})
  requests := object.get(resources, "requests", {})
  not object.get(requests, "memory", false)
  msg := sprintf("Container %q must define a memory request", [container.name])
}

violation contains {"msg": msg} if {
  container := containers[_]
  resources := object.get(container, "resources", {})
  limits := object.get(resources, "limits", {})
  not object.get(limits, "cpu", false)
  msg := sprintf("Container %q must define a CPU limit", [container.name])
}

violation contains {"msg": msg} if {
  container := containers[_]
  resources := object.get(container, "resources", {})
  limits := object.get(resources, "limits", {})
  not object.get(limits, "memory", false)
  msg := sprintf("Container %q must define a memory limit", [container.name])
}

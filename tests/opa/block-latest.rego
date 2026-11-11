package k8sblocklatest

violation contains {"msg": msg} if {
  container := input.review.object.spec.containers[_]
  regex.match("(^|/)[^/]+:latest(@.*)?$", container.image)
  msg := sprintf("Container image %q uses the forbidden latest tag", [container.image])
}

violation contains {"msg": msg} if {
  container := input.review.object.spec.initContainers[_]
  regex.match("(^|/)[^/]+:latest(@.*)?$", container.image)
  msg := sprintf("Init container image %q uses the forbidden latest tag", [container.image])
}

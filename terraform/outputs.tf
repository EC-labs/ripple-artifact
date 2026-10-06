output "vars" {
  value = {
    k8s-master = {
        publicIP = aws_eip.master.public_ip
        privateIP = aws_instance.ripple_master.private_ip
    }
    k8s-worker1 = {
        publicIP = aws_eip.worker1.public_ip
        privateIP = aws_instance.ripple_worker1.private_ip
    }
    k8s-worker2 = {
        publicIP = aws_eip.worker2.public_ip
        privateIP = aws_instance.ripple_worker2.private_ip
    }
  }
}

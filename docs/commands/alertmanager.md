# Monitoring Commands

Install or upgrade the stack:

```bash
helmfile -f k8s/operators/helmfile.yaml.gotmpl -e local \
  -l name=kube-prometheus-stack sync
```

Check the runtime and configuration:

```bash
helm list -n monitoring
kubectl get pods -n monitoring
kubectl get prometheus,alertmanager -n monitoring
kubectl get servicemonitor,prometheusrule -n monitoring
kubectl get application platform-observability -n argocd
```

Open the UIs:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-alertmanager 9093:9093
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Read the Grafana admin password:

```bash
kubectl get secret kube-prometheus-stack-grafana -n monitoring \
  -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

# osiris

Build log aggregation API.

## About

The Osiris API is build aggregator service which gathers build logs from the [OpenShift] and stores them into [Ceph].

## What

It comes accompanied by [observer] -- [OpenShift] namespace event watcher which filters **build events** and triggers appropriate endpoints (see [build api schema]). The rest is handled by Osiris API.

Osiris API currently gathers build logs only from its own namespace. That is, both api and the [observer] are in the same namespace and collaborate. (see [Future Ideas](#future-ideas))

## Api

The Osiris API has built in [swagger](https://swagger.io/) spec along with request / payload examples and query parameter documentation. It is recommended to check it out once the API is deployed to get familiar with the schema.

## How to deploy

All YAML templates that are required to deploy Osiris API are present in the [openshift](openshift/) directory. Note that templates require proper credentials which are taken from [configMap](openshift/configMap-template.yaml), which has to be deployed first with the right parameter setting.

To list configMap template parameters:

`oc process --parameters -f openshift/configMap-template.yaml`

To process the tamplate and pass the parameters (`oc process -h` for more info):

`oc process -p <key>=<value> -f openshift/configMap-template.yaml`

Alternatively, when the template is already loaded in [OpenShift] cluster:

`oc process -p <key>=<value> osiris-configmap | oc apply -f -`

<br>

Similiarly for other templates.

## Future Ideas

- It should be possible in the future to deploy Osiris API to a separate namespace and register multiple observers from different namespaces.

- It should also be possible for observer to pass the build log directly in the request data, so that Osiris API won't need to have access to that namespace.

- Another possibility is that Osiris API registers observers along with their credentials and use those credentials to access the namespace the observer is in and gather relevant build logs.

# Osiris API

This is a project demonstrating the basic structure of a API Service as used by the Thoth-Station. The service itself exports Prometheus metrics, and is instrumented to send Jaeger tracing.

The gRPC server is using a self signed TLS certificate.

## installing dependencies

You should know it by now: `pipenv install`

## run the OpenAPI Service locally

`OSIRIS_DEBUG=1 OSIRIS_API_APP_SECRET_KEY=start123 gunicorn thoth.osiris.openapi_server:app`

## run the gRPC Service

### Generate X.509 Certificates

```shell
openssl req -newkey rsa:2048 -nodes -keyout certs/tls.key -x509 -days 365 -out certs/tls.crt -config <(
cat <<-EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
req_extensions = req_ext
distinguished_name = dn

[ dn ]
C=
L=
CN=

[ req_ext ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1=localhost
EOF
)
```

### run locally

`OSIRIS_DEBUG=1 OSIRIS_API_APP_SECRET_KEY=start123 PYTHONPATH=. ./thoth/osiris/grpc_server.py` Check for the hostname the demo client is communication with!

### Generate GRPC code (optinal)

You could generate all the files required for gRPC client and server: `./run_codegen.py`

### Deploy to OpenShift

The repository contains templates for deploying the Osiris API to OpenShift. The TLS key and certificate are mounted into the gRPC server pod from a secret.

## run Jaeger locally

```shell
podman run --rm -ti -e COLLECTOR_ZIPKIN_HTTP_PORT=9411 \
    -p 5775:5775/udp \
    -p 6831:6831/udp \
    -p 6832:6832/udp \
    -p 5778:5778 \
    -p 16686:16686 \
    -p 14268:14268 \
    -p 9411:9411 \
    jaegertracing/all-in-one:latest`
```

[build api schema]: osiris/schema/build.py
[ceph]: https://ceph.com/
[observer]: https://github.com/thoth-station/osiris-build-observer
[openshift]: https://www.openshift.com/

# osiris

Build log aggregation API.

## About

The Osiris API is build aggregator service which gathers build logs from the [OpenShift] and stores them into [Ceph].

## What

It comes accompanied by [observer] -- [OpenShift] namespace event watcher which filters __build events__ and triggers appropriate endpoints (see [build api schema]).
The rest is handled by Osiris API.

Osiris API currently gathers build logs only from its own namespace. That is, both api and the [observer] are in the same namespace and collaborate. (see [Future Ideas](#future-ideas))

## Api

The Osiris API has built in [swagger](https://swagger.io/) spec along with request / payload examples and query parameter documentation. It is recommended to check it out
once the API is deployed to get familiar with the schema.

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



[build api schema]: osiris/schema/build.py
[Ceph]: https://ceph.com/
[observer]: https://github.com/thoth-station/osiris-build-observer
[OpenShift]: https://www.openshift.com/

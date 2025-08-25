from influxdb_client import InfluxDBClient
client = InfluxDBClient(url="http://host.docker.internal:8086", token="Ot182dX9zAc648STtxQvK22l_Qs0e2Io3XBhywV5yyyez79w-wzJFC5cSiooSgR8e9IV_GO-1DrcZziHTtQLEg==", org="abacus-demo",timeout=120)
query_api = client.query_api()
query = ''' |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "Temperature")
  |> limit(n: 20)'''
result = query_api.query(org="abacus-demo", query=query)

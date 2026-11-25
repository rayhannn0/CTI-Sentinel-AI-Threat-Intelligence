const config = {
  _id: "rs0",
  members: [
    {_id: 0, host: "mongo1:27017", priority: 2},
    {_id: 1, host: "mongo2:27017", priority: 1},
    {_id: 2, host: "mongo3:27017", priority: 1}
  ]
};
try { printjson(rs.initiate(config)); }
catch (e) {
  if (String(e).includes('already initialized') || e.codeName === 'AlreadyInitialized')
    print('Replica set already initialized.');
  else throw e;
}

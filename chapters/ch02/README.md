# How to use the example application

## Basic app flow

1. Run `make package deploy` to build and deploy the application.
2. Port-forward the timeline service to local port `8000`.
3. Open `http://localhost:8000/docs` in your browser.
4. Invoke `/dev/generateload` with the payload below.

```json
{
  "num_users": 10000,
  "num_posts": 300000,
  "num_follows": 800000,
  "seed": 42,
  "post_activity_bands": [
    { "user_percent": 1, "value_percent": 25 },
    { "user_percent": 9, "value_percent": 45 },
    { "user_percent": 30, "value_percent": 25 },
    { "user_percent": 60, "value_percent": 5 }
  ],
  "follow_bands": [
    { "user_percent": 1, "value_percent": 40 },
    { "user_percent": 9, "value_percent": 35 },
    { "user_percent": 30, "value_percent": 20 },
    { "user_percent": 60, "value_percent": 5 }
  ]
}
```

5. After a minute, invoke `/v1/timeline/{profile_id}` with a profile id such as `100`.
6. Port-forward the Jaeger query service to local port `16686`.
7. Search for tag `app.profile_id=123` to see the trace.

## Stream learning flow

This repo also includes a simple Redis stream demo:

1. Generate load using `/dev/generateload`.
2. Watch the app logs while the rows are inserted.
3. Invoke `/dev/sync`.
4. `/dev/sync` reads posts from the database, fans each post out to follower-specific message events, and writes those events into the Redis `posts` stream.
5. Run the consumer job from `k8s/stream-consumer-job.yaml`.
6. The job reads the `posts` stream from the beginning in batches, writes each delivered `post.id` into `message:<user_id>` in the `messagebox` Redis instance, and exits when the backlog is drained.

Example commands:

```bash
kubectl apply -f k8s/stream-consumer-job.yaml
kubectl logs -n cobrakai job/stream-consumer
```

If you want to run the job again, delete and recreate it:

```bash
kubectl delete job -n cobrakai stream-consumer
kubectl apply -f k8s/stream-consumer-job.yaml
```

Notes:

- This works well as a learning flow because the consumer is intentionally simple and drains the whole stream from `0-0`.
- Re-running the job replays all events currently present in Redis.
- Message boxes are Redis sets, so reprocessing the same delivery keeps inbox entries unique.
- If `/dev/sync` is triggered more than once, the same database posts will be appended to the Redis stream again.

To inspect message boxes with `redis-cli`:

```bash
redis-cli -h messagebox.cobrakai.svc.cluster.local KEYS 'message:*'
redis-cli -h messagebox.cobrakai.svc.cluster.local SMEMBERS message:123
```

## Tweet APIs

- Create: `POST /tweet/{sender_id}` with body `{ "text": "hello" }` returns `{ "message": "Tweet created" }`
- Get one: `GET /tweet/{id}` returns `sender_id`, `text`, `timestamp`
- Get many: `POST /tweet` with body like `[1, 2, 3]` returns an array of found tweet objects

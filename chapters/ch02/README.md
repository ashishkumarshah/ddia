How to use the example application.

1. make package deploy -> This will build and install the application.
2. portforward the time line service to local port 8000 (or anything)
3. open localhost:8000/docs in your browser, open the generatepayload endpoint and try it out in the UI with the below payload.
```
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
4. After a minute now invoke the the get time line endpoint with a profile id lets say 100.

5. port forward the jaeger query service to to 16686 (or anything)
6. search for tag -> app.profile_id=123 -> You should see the trace.
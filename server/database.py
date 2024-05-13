from prisma import Prisma
import redis

db = Prisma()
redis = redis.from_url("redis://localhost:6379")
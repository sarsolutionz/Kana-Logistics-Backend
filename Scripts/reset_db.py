import os

from django.contrib.auth import get_user_model

User = get_user_model()

cmd = "rm AdminApp/migrations/00*"
os.system(cmd)

cmd = "rm AuthApp/migrations/00*"
os.system(cmd)

cmd = "rm MemberApp/migrations/00*"
os.system(cmd)

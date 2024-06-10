cd server
pip install -r requirements.txt
prisma db push
python main.py# Check if Redis Server is installed, if not, install it
if ! command -v redis-server &> /dev/null
then
    echo "Redis Server could not be found, installing..."

    # Add the Redis repository GPG key
    curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg

    # Add the Redis repository
    echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list

    # Update the package list
    sudo apt-get update

    # Install Redis Server
    sudo apt-get install redis -y
fi

# Start Redis Server
redis-server

# Navigate to the server directory
cd server

# Install Python dependencies
pip install -r requirements.txt

# Apply Prisma schema changes to the database
prisma db push

# Run the main Python script
python main.py

host=$1
shift
port=$1
shift
timeout=${1:-30}

echo "⏳ Waiting for $host:$port (timeout: $timeout sec)"
for ((i=0;i<timeout;i++)); do
    nc -z "$host" "$port" && echo "✅ $host:$port is up!" && exit 0
    sleep 1
done

echo "❌ Timeout reached for $host:$port"
exit 1
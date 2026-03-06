FROM node:20-alpine

WORKDIR /app

COPY . /app

RUN if [ -f package.json ]; then npm install; else echo "No package.json yet - mount source during development."; fi

EXPOSE 3000

CMD ["sh", "-c", "if [ -f package.json ]; then npm run dev -- --host 0.0.0.0 --port 3000; else echo 'No frontend app found. Add package.json to run.' && tail -f /dev/null; fi"]

# Spotify Music Analysis Streamlit App

This Streamlit application provides an interactive dashboard for exploring and analyzing Spotify music data.

## Features

- Track analysis with popularity distribution and audio features
- Artist analysis with popularity metrics and genre exploration
- Overview of potential modeling approaches for music data

## Running with Docker

The application is containerized using Docker, making it easy to deploy and run consistently across different environments.

### Prerequisites

- Docker and Docker Compose installed on your system
- The Spotify dataset files in the `data/raw` directory of the main project

### Starting the Application

From the root directory of the project, run:

```bash
docker-compose up -d
```

This will:
1. Build the Streamlit application container
2. Mount the data directory
3. Start the Streamlit server on port 8501

### Accessing the Application

Once the container is running, access the application at:

```
http://localhost:8501
```

## Development

To make changes to the application:

1. Modify the `app.py` file
2. Rebuild the Docker container:
   ```bash
   docker-compose build streamlit
   ```
3. Restart the service:
   ```bash
   docker-compose up -d
   ```

## Future Enhancements

- Add user authentication
- Implement the modeling approaches described in the app
- Add data visualization export capabilities
- Connect to a database for storing processed results 
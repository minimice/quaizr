# To build this image, run 
# docker build -t quaizr-app:0.0.1 .
#
# To run this image, run
# docker run -p 80:80 -e GOOGLE_API_KEY="YOUR-GOOGLE-API-KEY" quaizr-app:0.0.1
#
# To push this image to docker hub, run
# docker push YOUR-DOCKER-USERID/quaizr-app:0.0.1
# 
# Once that is done, you can easily deploy it as a cloud run function by deploying the image from dockerhub
# Remember to set the GOOGLE_API_KEY environment variable

# Use Python 3.11 slim image
FROM python:3.11.14-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY app.png .
COPY questions.csv .
COPY helpers.py .

# Expose port 80
EXPOSE 80

# Set environment variable for Streamlit to run on port 80
ENV STREAMLIT_SERVER_PORT=80
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD ["streamlit", "run", "app.py", "--browser.gatherUsageStats=false", "--server.port=80", "--server.address=0.0.0.0"]
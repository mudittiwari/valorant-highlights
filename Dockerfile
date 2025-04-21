# Start from a lightweight Miniconda base
FROM continuumio/miniconda3

# Set working directory
WORKDIR /app

# Copy everything into the container
COPY . /app

# Copy and install the conda environment
COPY environment.yml .

# RUN apt-get update && apt-get install -y \
#     portaudio19-dev \
#     && rm -rf /var/lib/apt/lists/*


# Create conda environment
RUN conda env create -f environment.yml
RUN conda install -n highlights -c conda-forge ffmpeg
# Activate conda environment
SHELL ["conda", "run", "-n", "highlights", "/bin/bash", "-c"]


# Install any pip-only dependencies if needed
# RUN pip install some-pip-only-package

# Set environment to use our env by default
ENV PATH /opt/conda/envs/highlights/bin:$PATH

# Expose FastAPI port
EXPOSE 8082

# Default command: run FastAPI (can be overridden in docker-compose)
# CMD ["conda", "run", "-n", "highlights", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8082", "--log-level", "info"]

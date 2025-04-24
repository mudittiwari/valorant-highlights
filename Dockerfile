FROM continuumio/miniconda3
WORKDIR /app
COPY . /app
COPY cpu-env.yml .

# RUN apt-get update && apt-get install -y \
#     portaudio19-dev \
#     && rm -rf /var/lib/apt/lists/*

RUN conda env create -f cpu-env.yml
RUN conda install -n highlights -c conda-forge ffmpeg
SHELL ["conda", "run", "-n", "highlights", "/bin/bash", "-c"]

ENV PATH /opt/conda/envs/highlights/bin:$PATH
EXPOSE 8082

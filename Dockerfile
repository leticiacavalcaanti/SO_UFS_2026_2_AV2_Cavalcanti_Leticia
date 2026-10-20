FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        procps sysstat strace util-linux lsb-release \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir numpy==2.1.3 matplotlib==3.9.2 markdown==3.7

WORKDIR /work
COPY requirements.txt /work/requirements.txt
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/work
CMD ["bash"]

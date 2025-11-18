FROM nvidia/cuda:12.0-devel-ubuntu20.04

# Install Go
RUN apt-get update && apt-get install -y \
    ca-certificates \
    git \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN wget -qO- https://golang.org/dl/go1.21.linux-amd64.tar.gz | tar -C /usr/local -xzf -
ENV PATH="/usr/local/go/bin:${PATH}"

# Install MuPDF tools for PDF processing
RUN apt-get update && apt-get install -y \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o pru-engine ./cmd/pru-engine

# Expose application port
EXPOSE 8080

CMD ["./pru-engine"]
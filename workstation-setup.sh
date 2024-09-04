#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to print messages
print_message() {
    echo "------------------------------"
    echo "$1"
    echo "------------------------------"
}

# Update and Upgrade
print_message "Updating and Upgrading the system"
sudo apt update && sudo apt upgrade -y

# Install essential tools
print_message "Installing essential tools"
sudo apt install -y build-essential cmake git htop iotop nvtop linux-tools-generic software-properties-common zram-config

# Install HWE Kernel
print_message "Installing HWE Kernel"
sudo apt install -y linux-generic-hwe-22.04

# Optimize SSD
print_message "Optimizing SSD"
sudo systemctl enable fstrim.timer

# CPU Optimization
print_message "CPU Optimization"
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
sudo systemctl disable ondemand

# Memory Management
print_message "Optimizing Memory Management"
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# I/O Scheduler (assuming NVMe SSD, adjust if different)
print_message "Setting I/O Scheduler"
for i in {0..8}; do echo 'none' | sudo tee /sys/block/nvme${i}n1/queue/scheduler; done
for i in {0..8}; do cat /sys/block/nvme${i}n1/queue/scheduler; done

# Network Optimization
print_message "Network Optimization"
echo 'net.core.default_qdisc=fq' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control=bbr' | sudo tee -a /etc/sysctl.conf

# Install NVIDIA Drivers and CUDA
print_message "Installing NVIDIA Drivers and CUDA"
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update
sudo apt install -y nvidia-driver-535 nvidia-utils-535

# Install CUDA 12.2
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-2

# Set up CUDA environment variables
echo 'export PATH=/usr/local/cuda-12.2/bin${PATH:+:${PATH}}' >> $HOME/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}' >> $HOME/.bashrc

# Install Docker
print_message "Installing Docker"
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce
sudo usermod -aG docker $USER

# Optimize Docker
print_message "Optimizing Docker"
echo '{
    "storage-driver": "overlay2",
    "live-restore": true
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker

# Install Miniconda
print_message "Installing Miniconda"
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
echo 'export PATH="$HOME/miniconda/bin:$PATH"' >> $HOME/.bashrc
source $HOME/.bashrc
conda init

# Update GCC and install Clang
print_message "Updating GCC and installing Clang"
sudo apt install -y gcc-11 g++-11 clang

# Set up alternatives for GCC and G++
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 110 --slave /usr/bin/g++ g++ /usr/bin/g++-11
sudo update-alternatives --config gcc

# Install development tools
print_message "Installing development tools"
sudo apt install -y gdb valgrind

# Install Ollama
print_message "Installing Ollama"
curl -O https://ollama.com/download/Ollama-linux.zip
unzip Ollama-linux.zip
sudo mv ollama /usr/local/bin/ollama

# Final system update
print_message "Final system update"
sudo apt update && sudo apt upgrade -y

# Clean up
print_message "Cleaning up"
sudo apt autoremove -y

print_message "Setup complete! Please reboot your system."

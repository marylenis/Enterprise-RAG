#!/usr/bin/env python3
"""
Enterprise RAG Integration Test Runner

This script provides a convenient way to run integration tests with proper
environment setup and cleanup.
"""

import os
import sys
import argparse
import subprocess
import time
import signal
from pathlib import Path


def setup_test_environment():
    """Set up the test environment"""
    print("Setting up test environment...")

    # Set environment variables
    env_vars = {
        "TESTING": "true",
        "INTEGRATION_TEST": "true",
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "test-key-for-testing"),
        "PYTHONPATH": str(Path(__file__).parent.parent),
        "QDRANT_COLLECTION": "test_enterprise_docs",
        "FALKORDB_GRAPH": "test_enterprise_knowledge",
        "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
        "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
        "QDRANT_HOST": os.getenv("QDRANT_HOST", "localhost"),
        "QDRANT_PORT": os.getenv("QDRANT_PORT", "6333"),
        "FALKORDB_HOST": os.getenv("FALKORDB_HOST", "localhost"),
        "FALKORDB_PORT": os.getenv("FALKORDB_PORT", "6380"),
    }

    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key}={value}")

    # Create test data directory if it doesn't exist
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    print(f"Test data directory: {test_data_dir}")


def check_dependencies(args=None):
    """Check if required dependencies are available"""
    print("Checking dependencies...")

    # Check Python packages
    required_packages = [
        "pytest",
        "pytest-mock",
        "fastapi",
        "requests",
        "redis",
        "qdrant-client",
        "falkordb",
        "docker",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing_packages.append(package)

    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False

    # Check Docker
    if args and getattr(args, "no_services", False):
        print("  ✓ Docker (skipped, using existing services)")
    else:
        try:
            import docker

            client = docker.from_env()
            client.ping()
            print("  ✓ Docker")
        except Exception as e:
            print(f"  ✗ Docker (not available: {e})")
            return False

    return True


def start_services():
    """Start required services using Docker Compose"""
    print("Starting services...")

    docker_compose_file = Path(__file__).parent.parent / "docker-compose.yml"
    if not docker_compose_file.exists():
        print("  ✗ docker-compose.yml not found")
        return False

    # Start services
    try:
        cmd = [
            "docker-compose",
            "-f",
            str(docker_compose_file),
            "up",
            "-d",
            "redis",
            "qdrant",
            "falkordb",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ Failed to start services: {result.stderr}")
            return False

        print("  ✓ Services started")

        # Wait for services to be ready
        print("  Waiting for services to be ready...")
        time.sleep(30)  # Give services time to start

        return True

    except Exception as e:
        print(f"  ✗ Error starting services: {e}")
        return False


def stop_services():
    """Stop services"""
    print("Stopping services...")

    docker_compose_file = Path(__file__).parent.parent / "docker-compose.yml"
    if not docker_compose_file.exists():
        return

    try:
        cmd = ["docker-compose", "-f", str(docker_compose_file), "down"]

        subprocess.run(cmd, capture_output=True, text=True)
        print("  ✓ Services stopped")

    except Exception as e:
        print(f"  ✗ Error stopping services: {e}")


def run_tests(test_type="all", coverage=False, parallel=False, verbose=True):
    """Run the specified tests"""
    print(f"Running {test_type} tests...")

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add verbosity
    if verbose:
        cmd.append("-v")

    # Add coverage
    if coverage:
        cmd.extend(
            [
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=70",
            ]
        )

    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])

    # Add test selection
    integration_dir = Path(__file__).parent / "integration"

    if test_type == "all":
        cmd.append(str(integration_dir))
    elif test_type == "api":
        cmd.append(f"{integration_dir}/test_api_integration.py")
    elif test_type == "database":
        cmd.append(f"{integration_dir}/test_database_integration.py")
    elif test_type == "e2e":
        cmd.append(f"{integration_dir}/test_e2e_workflows.py")
    elif test_type == "docker":
        cmd.append(f"{integration_dir}/test_docker_integration.py")
    elif test_type == "frontend":
        cmd.append(f"{integration_dir}/test_frontend_backend.py")
    else:
        # Custom test path
        cmd.append(test_type)

    # Add additional markers
    cmd.extend(["-m", "not slow"])  # Skip slow tests by default

    # Run tests
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def cleanup():
    """Clean up test environment"""
    print("Cleaning up...")

    # Clean up test data
    test_data_dir = Path(__file__).parent / "test_data"
    if test_data_dir.exists():
        # Remove generated test files (keep original test files)
        for file in test_data_dir.glob("generated_*"):
            file.unlink()

    print("  ✓ Cleanup completed")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Enterprise RAG Integration Test Runner"
    )

    parser.add_argument(
        "--type",
        "-t",
        choices=["all", "api", "database", "e2e", "docker", "frontend"],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run tests with coverage report"
    )

    parser.add_argument(
        "--parallel", "-p", action="store_true", help="Run tests in parallel"
    )

    parser.add_argument(
        "--no-services",
        action="store_true",
        help="Don't start/stop services (use existing ones)",
    )

    parser.add_argument("--quiet", "-q", action="store_true", help="Reduce verbosity")

    parser.add_argument(
        "--cleanup-only", action="store_true", help="Only perform cleanup"
    )

    args = parser.parse_args()

    # Handle cleanup-only
    if args.cleanup_only:
        cleanup()
        stop_services()
        return

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal, cleaning up...")
        cleanup()
        stop_services()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Set up environment
        setup_test_environment()

        # Check dependencies
        if not check_dependencies(args):
            print("Dependency check failed. Please install missing dependencies.")
            sys.exit(1)

        # Start services if needed
        services_started = False
        if not args.no_services:
            if not start_services():
                print("Failed to start services.")
                sys.exit(1)
            services_started = True

        try:
            # Run tests
            success = run_tests(
                test_type=args.type,
                coverage=args.coverage,
                parallel=args.parallel,
                verbose=not args.quiet,
            )

            if success:
                print("\n✓ All tests passed!")
                sys.exit(0)
            else:
                print("\n✗ Some tests failed!")
                sys.exit(1)

        finally:
            # Stop services if we started them
            if services_started:
                stop_services()

    finally:
        # Always perform cleanup
        cleanup()


if __name__ == "__main__":
    main()

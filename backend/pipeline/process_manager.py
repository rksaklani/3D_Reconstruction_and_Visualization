"""Process manager for subprocess execution with logging."""

import os
import signal
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages subprocess execution with real-time logging and process groups."""
    
    @staticmethod
    def run_subprocess(
        cmd: List[str],
        log_path: Path,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[Path] = None
    ) -> Tuple[int, int]:
        """
        Run subprocess with real-time logging.
        
        Creates a process group using os.setsid for clean termination.
        Streams stdout and stderr to log file line by line.
        Writes command line to log file before execution.
        
        Args:
            cmd: Command and arguments
            log_path: Path to log file
            env: Environment variables (merged with os.environ)
            cwd: Working directory
            
        Returns:
            Tuple of (exit_code, pid)
            
        Raises:
            subprocess.SubprocessError: If subprocess fails to start
        """
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Merge environment variables
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)
        
        # Open log file for appending
        with log_path.open("a", encoding="utf-8", errors="replace") as lf:
            # Write command line
            lf.write("=" * 80 + "\n")
            lf.write(f"CMD: {' '.join(cmd)}\n")
            lf.write("=" * 80 + "\n")
            lf.flush()
            
            try:
                # Spawn subprocess with process group
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout
                    text=True,
                    bufsize=1,  # Line buffered
                    env=proc_env,
                    cwd=str(cwd) if cwd else None,
                    preexec_fn=os.setsid  # Create new process group
                )
                
                pid = proc.pid
                logger.info(f"Started subprocess PID={pid}, PGID={os.getpgid(pid)}")
                
                # Stream output line by line
                assert proc.stdout is not None
                for line in proc.stdout:
                    lf.write(line)
                    lf.flush()
                
                # Wait for completion
                exit_code = proc.wait()
                
                # Write exit code
                lf.write(f"\n[EXIT CODE: {exit_code}]\n")
                lf.flush()
                
                logger.info(f"Subprocess PID={pid} exited with code {exit_code}")
                
                return exit_code, pid
                
            except Exception as e:
                lf.write(f"\n[ERROR] Failed to execute subprocess: {e}\n")
                lf.flush()
                logger.error(f"Subprocess execution failed: {e}")
                raise
    
    @staticmethod
    def terminate_process_group(pid: int) -> None:
        """
        Terminate a process group.
        
        Sends SIGTERM to the entire process group identified by the PID.
        Handles ProcessLookupError gracefully (process already terminated).
        
        Args:
            pid: Process ID (also used as process group ID)
            
        Raises:
            OSError: If termination fails for reasons other than process not found
        """
        try:
            logger.info(f"Terminating process group PGID={pid}")
            os.killpg(pid, signal.SIGTERM)
            logger.info(f"Process group PGID={pid} terminated")
        except ProcessLookupError:
            logger.info(f"Process group PGID={pid} already terminated")
        except Exception as e:
            logger.error(f"Failed to terminate process group PGID={pid}: {e}")
            raise

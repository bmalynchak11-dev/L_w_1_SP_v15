"""
SP-LAB01: Задача 5. Конвеєр із pipe
Варіант 15 (Задача 5, набір 3)
"""

import os
import sys


def run_pipeline(stages: list[list[str]], stdout_path: str | None = None) -> list[int]:
    """
    Виконує конвеєр команд, з'єднуючи їх через os.pipe().
    Повертає список кодів завершення для кожного етапу.
    """
    if not stages:
        return []

    num_stages = len(stages)
    pipes = []
    
    # Створюємо канали між суміжними етапами: всього (num_stages - 1) каналів
    for _ in range(num_stages - 1):
        pipes.append(os.pipe())

    pids = []

    for i, argv in enumerate(stages):
        # Обов'язкове скидання буферів перед fork
        sys.stdout.flush()
        sys.stderr.flush()

        pid = os.fork()
        if pid == 0:
            # === Дочірній процес ===
            try:
                # 1. Налаштування stdin: для етапів i > 0 беремо читання з попереднього каналу
                if i > 0:
                    prev_read_fd = pipes[i - 1][0]
                    os.dup2(prev_read_fd, 0)

                # 2. Налаштування stdout:
                if i < num_stages - 1:
                    # Проміжні етапи пишуть у поточний канал
                    curr_write_fd = pipes[i][1]
                    os.dup2(curr_write_fd, 1)
                else:
                    # Останній етап пише у stdout_path, якщо він заданий
                    if stdout_path is not None:
                        out_fd = os.open(
                            stdout_path,
                            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                            0o644,
                        )
                        os.dup2(out_fd, 1)
                        os.close(out_fd)

                # 3. Закриваємо всі кінці створених каналів у дитині
                for r_fd, w_fd in pipes:
                    os.close(r_fd)
                    os.close(w_fd)

                # 4. Перевірка наявності команди
                if not argv:
                    os._exit(0)

                # 5. Заміна образу процесу на цільову програму
                os.execvpe(argv[0], argv, os.environ)

            except FileNotFoundError:
                sys.stderr.write(f"pysh: {argv[0]}: команду не знайдено\n")
                sys.stderr.flush()
                os._exit(127)
            except PermissionError:
                sys.stderr.write(f"pysh: {argv[0]}: немає дозволу на виконання\n")
                sys.stderr.flush()
                os._exit(126)
            except OSError as e:
                sys.stderr.write(f"pysh: {argv[0]}: {e.strerror}\n")
                sys.stderr.flush()
                os._exit(127)
            except Exception:
                os._exit(1)
        else:
            pids.append(pid)

    # === Батьківський процес ===
    # Закриваємо всі кінці каналів у батькові, щоб читачі отримали EOF
    for r_fd, w_fd in pipes:
        os.close(r_fd)
        os.close(w_fd)

    statuses = []
    # Очікуємо завершення кожного процесу за порядком
    for pid in pids:
        _, status = os.waitpid(pid, 0)
        if os.WIFEXITED(status):
            statuses.append(os.WEXITSTATUS(status))
        elif os.WIFSIGNALED(status):
            statuses.append(128 + os.WTERMSIG(status))
        else:
            statuses.append(1)

    return statuses
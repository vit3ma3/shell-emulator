# Ошибки vfs-save
vfs-save
vfs-save a b
vfs-save examples/vfs/nested
vfs-save README.md/snapshot
vfs-save output/stage3_errors
# повторное сохранение в тот же путь - ошибка, перезаписи нет
vfs-save output/stage3_errors

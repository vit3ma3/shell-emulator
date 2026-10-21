# Переименование файла
ls
mv readme.txt intro.txt
ls

# Перемещение файла в каталог
mv intro.txt documents/
ls documents

# Перемещение с переименованием
mv documents/intro.txt projects/first.txt
tree

# Ошибочные операции
mv missing.txt absent.txt
mv
mv projects
mv documents/notes.txt missing/
mv documents/notes.txt documents/report.txt
mv projects projects/demo
mv / documents
mv projects projects

# Сохранение изменённой VFS
vfs-save output/stage5_snapshot

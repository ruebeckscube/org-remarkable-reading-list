(setq default-book-directory "/path/to/folder/of/ebooks/and/pdfs/")
(setq reading-list-filename "reading-list.org")
(setq python-sync-script-directory "~/path/to/directory/containing/python/script/")

(defun get-org-book-link ()
  (let ((book-file (read-file-name "Enter file name: " default-book-directory)))
    (if (file-regular-p book-file)
        (concat "\n:FILE: [[file:" book-file "][Link to file]]")
      "")))

(defun get-org-book-irl ()
  (if (y-or-n-p "Do you have a physical copy? ")
      "\n:IRL: t"
    ""))

(setq org-capture-templates
      '(("b" "Book" entry (file reading-list-filename)
         "* UNREAD %^{TITLE}\n:PROPERTIES:\n:ADDED: %<[%Y-%02m-%02d]>%(get-org-book-link)%(get-org-book-irl)\n:END:%^{AUTHOR}p\n%?" :empty-lines 0)))

(setq org-agenda-custom-commands
      '(("u" todo "UNREAD")
        ("n" todo "NEXT")
        ("r" todo "READING")))

(add-to-list 'org-file-apps '("\\.epub\\'" . system))
(add-to-list 'org-file-apps '(directory . system))

(defun sync-reading-list-to-remarkable ()
  (interactive)
  (vterm)
  (vterm-send-string (cat "cd " python-sync-script-directory))
  (vterm-send-return)
  (vterm-send-string "export PIPENV_IGNORE_VIRTUALENVS=1") ; In case emacs has an active virtual env
  (vterm-send-return)
  (vterm-send-string "pipenv run python -W ignore sync-reading-list.py")
  (vterm-send-return)
  )

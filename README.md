# Org reading list with sync to reMarkable

These are the scripts/config I use for managing my reading list in org-mode and
syncing that list to my reMarkable tablet. I imagine it's a pretty unique use
case, so take these as inspiration rather than ready-to-use out of the box.

As-is, this supports
* tracking of current reading
* cueing books to read next
* tracking timestamps for starting/finishing a book
* syncing current reading to a reMarkable via the USB web interface
* and, for extra fun, an option to download your marginalia (notes) from the
  reMarkable as a pdf when you're done reading. Saves space on reMarkable,
  doesn't lose your notes, keeps everything nice and organized through file
  links in the org file.

The org portion was inspired by [this repository](https://github.com/lepisma/org-books)
among others.

# Installation

That said, if you happen to be another org+reMarkable user, and want to try
using this out of the box:

1. Requirements: python, pipenv, emacs, org-mode, vterm (emacs package)

2. Clone this repository, navigate to its directory, and
``` sh
pipenv install
```
to install python dependencies in the virtual environment.

2. Make an org file to hold your reading list (ideally in your `org-directory`).
   At the top, add
``` org
#+title: Reading List

#+TODO: UNREAD(u) NEXT(n) READING(r!) | READ(d!) REFERENCE(f)
```
and add the file to your org-

3. Copy the contents of `example-org-config.el` into your emacs `config.el`
   (somewhere after org is loaded) and replace the variable contents of the
   `setq` statements at the top with your desired directories (full path).
   Create the directories.

4. Rename `example-options.json` to `options.json` and again replace the
   variable contents. Make a top-level folder on your remarkable to hold synced
   files.

5. Create whatever kind of organization you want in your org file. I like to
   organize by fiction/nonfiction, then genre/topic. 

# Usage

## Create a book entry
If you have an ebook or pdf, put it into the directory you created for holding
book files. It can have subfolders etc, but since the organization is covered by
the org file, I keep it flat. In emacs, enter `M-x org-capture` (default `C-c n n`),
then press `b`
for Book. It will prompt you for the filename (should default to the directory
you set up, but you can add a book from anywhere on your computer) and other
metadata. If you want to cue it to read next, or mark it as currently reading,
change the todo status with `C-c C-t`. To refile, `C-c C-w` (in my case, to file
under appropriate genre/topic).

## See current reading status
Invoke `M-x org-agenda` (default `C-c n a`) and you should see three default
agenda views added by the org config. Press the corresponding key to see a list
of books currently holding that status, and in the agenda view you can update
their status with `C-c C-t`.

## Sync to reMarkable
With the reMarkable connected via USB, make sure the USB web interface is
enabled in Settings > Storage. With the reMarkable powered on and awake, invoke
`M-x sync-reading-list-to-remarkable`. Watch the magic happen, respond to
prompts! Any book marked READING since the last sync should automatically be
loaded onto the reMarkable, and any book marked DONE since the last sync should
prompt you asking if you want to download marginalia.

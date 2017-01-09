<div>
  <img src="https://upload.wikimedia.org/wikipedia/commons/0/04/Briefcase_font_awesome.svg" height=50 align="left" style="padding-top:15px; display:inline">
  <h1>jobsbox</h1>
</div>

### Dependencies
requests - `pip install requests`  
pyyaml - `pip install pyyaml`  
gmail - `pip install gmail`  

### Run
You can optionally email posts that include an address if you provide a template email  
**Edit `config.yml` to fit your needs**
- `use_email_file`: if you want to keep track of who has been emailed so they aren't emailed multiple times
- `password`: text file that has your gmail password
- `categories`: what keywords you want to search on 
  - `email_primary`: what to say for the most-encountered category
  - `email_secondary`: smaller blurb if this category has not been mentioned as much as others. All `email_secondary` fields will be joined and comma separated
  
- `email`
  - `from`: your gmail address
  - `subject`, `body`: template for emails. Intersperse with `{ site }`, `{ company }`, `{ email_primary }`, and `{ email_secondary }` as desired and they will be replaced dynamically
  
Optionally set up a cron job to have it run regularly  
`crontab -e`  
`30 12  * * *   cd /path/to/jobsbox/ && .//path/to/jobsbox/Scraper.py`
-> will run everyday at 12:30

### Output/Other files
Logs will be output to the `logs` directory including who was emailed, if new sources were encountered, etc. 
If history is enabled `history.json` will be in the root directory and include much of the same information, except on a running basis

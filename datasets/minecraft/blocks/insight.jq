map(to_entries) | add | group_by(.key) 
   | map({ (.[0].key): [.[].value] | unique }) 
   | add
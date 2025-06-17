=begin
  A ruby script to run on your GitLab instance to return some basic information about every mirror repository that is currently
  in a 'failed' or 'unsuccessful' stage. Good for easily identifying repositories that need troubleshooting.

  Author: Jack Harris
=end

Project.find_each() do |project|
	has_push = project.remote_mirrors.any?
	has_pull = project.mirror?

	if has_push || has_pull		
		pushMirror = project.remote_mirrors

		# this URL is where we found the cred bug. the code gets rid of creds!
		cleanUrl = nil
		pushMirror.each do |m|
			next if m.update_status == 'finished'

			pushUrl = m.url
			
			# parses plaintext username and password out of the url
			# URI parses into its identifiers (username, password, host, path)
			# `.tap` performs operations and yields immediate results. 
			# here, `u` is the uri object from before
			cleanUrl = URI.parse(pushUrl).tap { |u| u.user = u.password = nil }.to_s
		end

		if project.mirror?
			next if project.import_status == 'finished'

			pullUrl = project.import_url	
		end

		if cleanUrl != nil || pullUrl != nil
			# Necessary project info
			puts "\e[1mProject #{project.id}, #{project.name}\e[0m"

			if cleanUrl != nil
				puts "\e[31mPush mirror has raised an error. Details below: "
				puts " - Push Remote mirror URL: #{cleanUrl}\e[0m"
			end
			if pullUrl != nil
				puts "\e[31mPull mirror has raised an error. Details below: "
				puts " - Pull Remote mirror URL: #{pullUrl}\e[0m"
			end
	
			# creates hyperlink to repository
			basePath = "https://gitlab.domain.com/"
			projectPath = project.full_path
			projectUrl = basePath + projectPath
			puts "\n\e[1mGitLab Repository path: #{projectUrl}\e[0m"
				
			# last activity
			puts "Last activity: #{project.last_activity_at}"
				
			# mirror_successful_at
			puts "Latest check: #{project.last_repository_check_at}"
			puts "\n", "-" * 116
		end
	end		
end

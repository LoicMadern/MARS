require 'bibliothecary'
require 'json'

Bibliothecary.configure do |config|
    config.carthage_parser_host   = 'localhost:5000'
  end

puts Bibliothecary.analyse(ARGV[0]).to_json
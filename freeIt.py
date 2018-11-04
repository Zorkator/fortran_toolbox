#!/usr/bin/env python
"""Usage:
  freeIt [-v...] [options] [FILE...]
  freeIt (-h | --help)

Convert fixed format fortran files to free format.

Options:
  -h --help                     show this help screen.
  -o OUTFILE, --out OUTFILE     write output to file instead of dumping it to stdout.
  -v                            set verbosity of printed messages. Increase level by
                                repeating the option.
"""

import docopt, re

##############################
class LineConverter(object):
##############################
  _normal  = re.compile( r'^[\s\d]{5}\s+[^!\s]|^\s*$' ).match
  _comment = re.compile( r'^[^\d\s#]|^\s*!' ).match
  _preproc = re.compile( r'^#' ).match
  
  def __init__( self ):
    self._ppContinue = False
    self._lineBuff   = None
    self._comments   = []


  def put( self, line ):
    if self._ppContinue:
      self._ppContinue = line.endswith('\\')
      print( line )
    else:
      line = line[:6].replace( '\t', ' '*6 ) + line[6:] #< handle tab-indented lines

      if   self._normal( line )   : self.normal( line )
      elif self._comment( line )  : self.comment( line )
      elif self._preproc( line )  : self.preproc( line )
      elif not line[5:6].isspace(): self.merge( line )
      else                        : raise TypeError( line )
      

  def normal( self, line ):
    self.flush()
    self._lineBuff = line


  def comment( self, line ):
    if line[0].isspace(): self._comments.append( line.rstrip() )
    else                : self._comments.append( '!' + line[1:].rstrip() )


  def preproc( self, line ):
    self.flush()
    print( line )
    self._ppContinue = line.endswith('\\')


  def merge( self, line ):
    buffered = self._lineBuff or ''
    line     = line[6:]
    self._lineBuff = buffered + ' &\n' + line


  def flush( self ):
    if self._lineBuff != None:
      print( self._lineBuff.rstrip() )
    if self._comments:
      print( '\n'.join( self._comments ) )

    self._lineBuff    = None
    self._comments[:] = []



############################
class FileCrawler(object):
############################
  _tryCodecs = ['utf-8', 'latin-1']

  @staticmethod
  def _getStream( fileName, codec ):
    import codecs
    binaryStream = open( fileName, 'rb' )
    return codecs.getreader(codec)(binaryStream)


  def _readFile( self, fileName ):
    for codec in self._tryCodecs:
      try:
        with self._getStream( fileName, codec ) as stream:
          lines = stream.readlines()
          self._log.info( "scanning {0} [{1}]".format( fileName, codec ) )
          return lines
      except UnicodeError:
          pass
    else:
      raise UnicodeError( "unable to decode {0}, giving up :-(".format( fileName ) )


  def __init__( self, **kwArgs ):
    import logging

    logging.basicConfig()
    self._log = logging.getLogger( self.__class__.__name__ )
    self._log.setLevel( logging.WARNING - kwArgs['-v'] * 10 )
    self._log.debug( kwArgs )

    fileSet = set( kwArgs['FILE'] )
    map( self.scanFile, fileSet )
    self._log.info( 'done' )


  def scanFile( self, fileName ):
    try:
      conv = LineConverter()
      for num, line in enumerate( self._readFile( fileName ), start=1 ):
        conv.put( line.splitlines()[0] )
      conv.flush()

    except IOError as e:
      self._log.error( "{0} skipped: {1}".format( fileName, e ) )
    except Exception as e:
      self._log.error( "error around line {0}:".format( num ) )
      raise


if __name__ == "__main__":
  opts = docopt.docopt( __doc__ )
  FileCrawler( **opts )


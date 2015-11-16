# Twoline Logwatch

Display messages on your 2-line LCD screen when log messages are found matching patterns you specify.

## Requirements

* [twoline](https://github.com/coddingtonbear/twoline)

## Installation

Install from pip

```
pip install twoline-logwatch
```

## Use

Just run `twoline-logwatch` with two arguments: the path to a configuration file, and the HTTP address of your Twoline server.

If you had your configuration file stored at `/etc/twoline-logwatch.conf` and your Twoline server was running at `http://127.0.0.1:6224`, you could run:

```
twoline-logwatch /etc/twoline-logwatch.conf http://127.0.0.1:6224
```

For more information about the configuration file format, see below.

## Configuration

Twoline Logwatch is configured using a simple JSON dictionary file having a single top-level key -- `files` -- itself having sub-keys for each path to watch, and each of those subkeys having subkeys for each of the regular expression patterns to match.  Each of those patterns has a single [message object](https://github.com/coddingtonbear/twoline#message-object) value, and the message object's `message` field can use any named groups in the aforementioned regular expression pattern as string formatting fields.  This is quite a mouthful, but the below examples should make this a bit clearer.

Twoline Logwatch works by running `tail -f` on paths you specify; checking each line of output against a set of regular expressions you set.

```json
{
    "files": {
        "/path/to/file/to/watch": {
            "<REGULAR EXPRESSION TO MATCH>": {
                /* Any standard message object */
            }
        }
    }
}
```

### Meta Options

Each [message object](https://github.com/coddingtonbear/twoline#message-object) can also contain a key `meta` dictionary having any number of keys used for overriding the default behavior of Twoline Logwatch when generating the message.

* `message_name`: The message name under which to publish this message in Twoline.  By default, Twoline Logwatch publishes messages under a single name "logwatcher".  Since all messages share a single name, only one message will be displayed at a time unless you take special efforts to define a different `message_name` for each potential message.  See "Displaying multiple messages simultaneously" below for more information.  Note that `message_name` here is exactly the same thing as `message_id` described in Twoline's documentation.
* `method`: The HTTP method to use when sending the request to Twoline.  By default, each message sent to Twoline will be sent using the `PUT` method, but for complex interactions (see "Printing a message and later deleting it" below) you can override the HTTP method using this option.

### Examples

#### Printing a message when an SSH connection is established

On most systems, log messages are written to `/var/log/auth.log`, and the log message written when a user logs in via SSH will be something like:

```
Nov 15 19:27:49 morse sshd[4049]: pam_unix(sshd:session): session opened for user somebodyspecial by (uid=0)
```

If you were to create a configuration as follows:

```json
{
    "files": {
        "/var/log/auth.log": {
            ".*sshd.*pam_unix.*session opened for user (?P<username>[a-zA-Z0-9-_]+).*": {
                "message": "SSH Login by\n{username}"
            }
        }
    }
}
```

when a user logs in via SSH, the following message would be displayed on the LCD screen:

```
SSH Login by
somebodyspecial
```

Note that, for simplicity's sake, the regular expression matches only enough to make the match turn up few (probably no) false positives, but you could make it quite a lot more rigid if you desired.  Also take note of how the named group `username` was used in the message itself.

#### Printing a message and later deleting it

Say that you have a log file `/var/log/cookiejar.log` that includes messages like the following:

```
Nov 15 19:27:49 User somebodyspecial has put his or her hand in the cookiejar.
Nov 15 19:28:22 User somebodyspecial has removed his or her hand from the cookiejar.
```

And you wanted to display a message on the screen *only* while the user had his or her hand in the cookiejar (between 19:27:49 and 19:28:22), you could write a configuraiton as follows:

```json
{
    "files": {
        "/var/log/cookiejar.log": {
            ".*User (?P<username>[a-zA-Z0-9-_]+) has put his or her hand in the cookiejar": {
                "message": "Cookiejar!\n{username}"
            }
            ".*User (?P<username>[a-zA-Z0-9-_]+) has removed his or her hand from the cookiejar": {
                "meta": {
                    "method": "delete"
                }
            }
        }
    }
}
```

#### Displaying multiple messages simultaneously

By default Twoline Logwatch always publishes under the "logwatcher" message name, so any messages that are displayed will overwrite the previously-displayed one, but you can easily change the behavior such that two messages are displayed simultaneously (Twoline itself will alternate between them).

Combining the above "Printing a message when an SSH connection is established" and "Printing a message and later deleting it" messages into a single configuration, you can allow messages from each to be displayed simultaneously by defining a separate `message_name` for each like the below:
```json
{
    "files": {
        "/var/log/cookiejar.log": {
            ".*User (?P<username>[a-zA-Z0-9-_]+) has put his or her hand in the cookiejar": {
                "message": "Cookiejar!\n{username}",
                "meta": {
                    "message_name": "cookiejar"
                }
            }
            ".*User (?P<username>[a-zA-Z0-9-_]+) has removed his or her hand from the cookiejar": {
                "meta": {
                    "method": "delete",
                    "message_name": "cookiejar"
                }
            }
        },
        "/var/log/auth.log": {
            ".*sshd.*pam_unix.*session opened for user (?P<username>[a-zA-Z0-9-_]+).*": {
                "message": "SSH Login by\n{username}",
                "meta": {
                    "message_name": "ssh_login"
                }
            }
        }
    }
}
```

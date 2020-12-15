import sys
import yaml
import psycopg2
import bcrypt
import getpass

"""
    TODOS:
        - password suggestion feature
        - creation of a new account
        - update a password
        - find all sites and apps connected to an email
        - find password for a site

"""


class PasswordManager:
    def __init__(self):
        try:
            f = open("config.yaml", "r")
            config = yaml.load(f, Loader=yaml.FullLoader)

            self.conn = psycopg2.connect(host=config['host'], port=config['port'],
                                         database=config['database'], user=config['user'], password=config['password'])
        except (Exception, psycopg2.Error) as e:
            print("Error occurred while connection to the database")

    def display_menu(self):
        ''' displays the menu '''
        print("\n")
        print("-"*36)
        print("-"*15, "Menu", "-"*15)
        print("-"*36)
        print("0. Exit or press ctrl + c")
        print("1. Enter new account")
        print("2. Update password")
        print("3. Find all sites and apps connected to an email")
        print("4. Find a password for a site")
        print("5. display all the information stored")

    def new_account(self):
        """ 
            adds new entry to the database
            Details needed:
                site name, username, email, password
        """
        site = input("Enter site name: ")
        username = input("Enter username: ")
        email = input("Enter email: ")
        pw = input("Enter password: ")

        query = f"""INSERT INTO accounts (site, username, email, password) VALUES (\'{site}\', \'{username}\', \'{email}\', \'{pw}\');"""

        cursor = self.conn.cursor()
        cursor.execute(query)

        # committing the changes
        self.conn.commit()
        cursor.close()

        print("new account created successfully👌\n")

    def update_password(self):
        """ update the old passworld with new one"""
        site = input("Enter site name whose password you want to change: ")
        password = input("Enter new password: ")
        confirm_pw = input("Confirm new password: ")

        if password:
            if password == confirm_pw:
                query = f"""UPDATE accounts SET password =\'{password}\' WHERE site=\'{site}\';"""

                cursor = self.conn.cursor()
                cursor.execute(query)

                # committing the changes

                self.conn.commit()
            else:
                print("The password does not match! Try again")
        else:
            print("Password can not be empty. Try again")

    def find_link_with_email(self):
        """Number 3
        Find all sites and apps connected to an email"""
        email = input("Enter the email: ")
        command = f"""select site FROM accounts WHERE email=\'{email}\';"""

        cursor = self.conn.cursor()
        cursor.execute(command)

        print("\nRESULTS\n")
        print("\tSITE")
        results = cursor.fetchall()
        if email:
            for i in results:
                print("\t" + i[0])
        else:
            print("empty email")

        # close the cursor
        cursor.close()

    def find_password(self):
        """Number 4
            Find a password for a site
        """
        site = input("Enter the site name: ")

        query = f"SELECT password FROM accounts WHERE site=\'{site}\';"

        cursor = self.conn.cursor()
        cursor.execute(query)

        print("\nRESULTS\n")
        print("PASSWORD")
        results = cursor.fetchall()
        if site:
            for i in results:
                print("\t" + i[0])
        else:
            print("Empty site name")
        cursor.close()

    def display_accounts(self):
        ''' display all the information in the database'''
        # returns all the data in the accounts table
        query = """SELECT * FROM accounts;"""

        cursor = self.conn.cursor()
        cursor.execute(query)
        info = cursor.fetchall()

        print("\n")
        print("RESULTS\n")
        print("SITE\t\tUSERNAME\tEMAIL\t\t\t\tPASSWORD")

        for i in info:
            print(f"{i[0]}\t\t{i[1]}\t{i[2]}\t\t{i[3]}")
        cursor.close()

    def main(self):
        """ get the choice e.g.: 1 to exit etc
            calls other function based on the input (a number chosen)
        """

        while True:
            try:
                self.display_menu()
                choice = int(input("choose a number: "))

                if choice == 0:
                    self.conn.close()
                    print("Closing things up. Exitting....")
                    sys.exit(0)
                elif choice == 1:
                    self.new_account()
                elif choice == 2:
                    self.update_password()
                elif choice == 3:
                    self.find_link_with_email()
                elif choice == 4:
                    self.find_password()
                else:
                    self.display_accounts()
            except (Exception, KeyboardInterrupt):
                print("sfasdasdasdasd")
                self.conn.close()
                sys.exit(0)

    def _encrypt_password(self, pw):
        """encrypts the password provided"""

        salt = bcrypt.gensalt()
        pw = bcrypt.hashpw(pw.encode("utf-8"), salt)

        # decode to utf-8
        # convert bytes into str
        return pw.decode("utf-8")

    def _create_new_master(self):
        """
            called when there is no master account
        """
        username = input("Create master username: ")

        master_password = ''

        while True:
            # enter password until they match
            try:
                password = getpass.getpass(prompt="create master password: ")
                confirm_pw = getpass.getpass(
                    prompt="confirm master password: ")

                if password:
                    if password == confirm_pw:
                        master_password = password
                        break
                    else:
                        print("Password don't match. Try again!")
                else:
                    print("Empty password isn't accepted.")
            except (Exception, KeyboardInterrupt):
                print("\nerror occurred. Please try again")
                sys.exit(0)

        # ensuring that the masterpassword is not empty or None
        if master_password:
            # encrypt password
            encrypted_pw = self._encrypt_password(master_password)

            # insert the new information into the database
            query = f"""INSERT INTO main (username, password) VALUES (\'{username}\', \'{encrypted_pw}\');"""

            cursor = self.conn.cursor()
            cursor.execute(query)
            # commit/save the changes
            self.conn.commit()

    def _authenticate(self, hashed_pw):
        """
            @param pw: password entered by user
            @param hashed_pw: password stored in the database
            return True if 'pw' matches 'hashed_pw'
                else False
        """

        # prevent eching of the password
        pw = getpass.getpass(prompt="Enter the password: ")
        match = bcrypt.checkpw(pw.encode("utf-8"), hashed_pw.encode("utf-8"))
        return match

    def authenticate_master(self):
        """ authenticate the access of the  """

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM main")

        # data[0][0] -> username; data[0][1] -> hashed_password
        data = cursor.fetchall()

        # check the main table is empty
        # if empty create new superuser
        if data == []:
            self._create_new_master()
            print("Exiting.....\nNow enter again as master")
            sys.exit(0)
        else:
            print(f"\nWelcome back. {data[0][0]}\n")

            chances = 3

            if self._authenticate(data[0][1]):
                while True:
                    self.main()
            else:
                print("Wrong password! Try again")


if __name__ == '__main__':
    pw = PasswordManager()
    pw.authenticate_master()

    # display_accounts()

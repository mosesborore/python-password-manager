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
        f = open("config.yaml", "r")
        config = yaml.load(f, Loader=yaml.FullLoader)

        self.conn = psycopg2.connect(host=config['host'], port=config['port'],
                                     database=config['database'], user=config['user'], password=config['password'])
        self.cursor = self.conn.cursor()

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
        """ """
        site = input("Enter site name: ")
        username = input("Enter username: ")
        email = input("Enter email: ")
        pw = input("Enter password: ")

        query = f"""INSERT INTO accounts (site, username, email, password) VALUES (\'{site}\', \'{username}\', \'{email}\', \'{pw}\');"""

        cursor = self.conn.cursor()
        cursor.execute(query)

        # committing the changes
        self.conn.commit()

    def update_password(self):
        """ update the old passworld with new"""
        site = input("Enter site name: ")
        pw = input("Enter password: ")
        confirm_pw = input("Confirm password: ")

        if pw == confirm_pw:
            query = f"""UPDATE accounts SET password =\'{pw}\' WHERE site=\'{site}\';"""

            cursor = self.conn.cursor()
            cursor.execute(query)
            # committing the changes
            self.conn.commit()

        else:
            print("The password does not match! Try again")

    def find_link_with_email(self):
        """Number 3
        Find all sites and apps connected to an email"""
        email = input("Enter the email: ")
        command = f"""select site FROM accounts WHERE email=\'{email}\';"""

        cursor = self.conn.cursor()
        cursor.execute(command)

        print("\nRESULTS\n")
        print("\tSITE")
        for i in cursor.fetchall():
            print("\t" + i[0])

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
        for i in cursor.fetchall():
            print("\t" + i[0])

    def display_accounts(self):
        ''' display all the information in the database'''
        # returns all the data in the accounts table
        query = """SELECT * FROM accounts;"""

        self.cursor.execute(query)
        info = self.cursor.fetchall()

        print("\n")
        print("RESULTS\n")
        print("SITE\t\tUSERNAME\tEMAIL\t\t\t\tPASSWORD")

        for i in info:
            print(f"{i[0]}\t\t{i[1]}\t{i[2]}\t\t{i[3]}")

    def main(self):
        """ get the choice e.g.: 1 to exit etc
            calls other function based on the input (a number chosen)
        """

        while True:
            try:
                self.display_menu()
                choice = int(input("choose a number: "))

                if choice == 0:
                    self.cursor.close()
                    sys.exit(0)
                elif choice == 1:
                    self.new_account()
                elif choice == 2:
                    self.update_password()
                elif choice == 3:
                    self.find_link_with_email()
                elif choice == 4:
                    self.find_password()
                elif choice == 5:
                    self.display_accounts()
                elif choice == 3:
                    self.find_link_with_email()
            except KeyboardInterrupt:
                sys.exit(0)

    def _encrypt_password(self, pw):
        """encrpts the password provided"""

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

        pw = ''
        confirm_pw = ''
        while True:
            # enter password until they match
            try:
                pw = input("Enter password: ")
                confirm_pw = input("Enter password: ")

                if pw == confirm_pw:
                    break
                else:
                    print("Password don't match. Try again!")
            except:
                print("error occurred. Please try again")
                continue

        # encrypt password
        encrypted_pw = self._encrypt_password(pw)

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

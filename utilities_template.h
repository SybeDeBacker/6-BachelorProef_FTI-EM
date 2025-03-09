class utilities
{
private:
    const char* your_ssid = "Your SSID";
    const char* your_password = "Your Password";
public:
    const char* ssid();
    const char* password();
};

const char* utilities::ssid()
{
    return your_ssid;
}

const char* utilities::password()
{
    return your_password;
}
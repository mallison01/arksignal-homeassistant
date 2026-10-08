from homeassistant import config_entries


class FakeFlow(config_entries.ConfigFlow, domain="fakestation"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return self.async_create_entry(title="Fake Tempest", data={})

""" Generic Example cog with a variety of features."""


from typing import override
import discord
from discord import app_commands
from discord.client import Client
from discord.ext import commands
from discord.interactions import Interaction
from discord.ui import LayoutView, Button
from loguru import logger


from oscar.ui.paginated_view import PaginatedView



class Examples(commands.Cog):
    """ Cog Class holding various examples"""
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        logger.info("Loaded Examples cog")

        # Generate sample data (64 items as requested)
        self.sample_data: list[dict[str, int|str]] = []
        statuses = ["Active", "Inactive", "Pending", "Error"]

        for i in range(1, 65):  # Example 1 to 64
            self.sample_data.append({
                "id": i,
                "name": f"Example {i}",
                "value": f"Val_{i:03d}",
                "status": statuses[(i - 1) % len(statuses)]
            })

    @app_commands.command(name='colors', description='display all text and background colors')
    async def colors(self, interaction: discord.Interaction):
        """Slash command to display all possible text and background colors"""

        embed: discord.Embed = discord.Embed(
            title='Text Colors',
            # pylint: disable=C0301 # (line-too-long)
            url='https://www.pythondiscord.com/pages/guides/python-guides/discord-messages-with-colors/',
            description="""
To be able to send a colored text, you need to use the ansi language for your code block and provide a prefix of this format before writing your text:
```
\\u001b[{format};{color}m
```
All possible formats are:
```ansi
• 0: \u001b[0;00mNormal\u001b[0m
• 1: \u001b[1;00mBold\u001b[0m
• 4: \u001b[4;00mUnderline\u001b[0m
```

All possible colors are:
```ansi
\u001b[1;30;40m Text \u001b[1;30;41m Text \u001b[1;30;42m Text \u001b[1;30;43m Text \u001b[1;30;44m Text \u001b[1;30;45m Text \u001b[1;30;46m Text \u001b[1;30;47m Text
\u001b[1;31;40m Text \u001b[1;31;41m Text \u001b[1;31;42m Text \u001b[1;31;43m Text \u001b[1;31;44m Text \u001b[1;31;45m Text \u001b[1;31;46m Text \u001b[1;31;47m Text
\u001b[1;32;40m Text \u001b[1;32;41m Text \u001b[1;32;42m Text \u001b[1;32;43m Text \u001b[1;32;44m Text \u001b[1;32;45m Text \u001b[1;32;46m Text \u001b[1;32;47m Text
\u001b[1;33;40m Text \u001b[1;33;41m Text \u001b[1;33;42m Text \u001b[1;33;43m Text \u001b[1;33;44m Text \u001b[1;33;45m Text \u001b[1;33;46m Text \u001b[1;33;47m Text
\u001b[1;34;40m Text \u001b[1;34;41m Text \u001b[1;34;42m Text \u001b[1;34;43m Text \u001b[1;34;44m Text \u001b[1;34;45m Text \u001b[1;34;46m Text \u001b[1;34;47m Text
\u001b[1;35;40m Text \u001b[1;35;41m Text \u001b[1;35;42m Text \u001b[1;35;43m Text \u001b[1;35;44m Text \u001b[1;35;45m Text \u001b[1;35;46m Text \u001b[1;35;47m Text
\u001b[1;36;40m Text \u001b[1;36;41m Text \u001b[1;36;42m Text \u001b[1;36;43m Text \u001b[1;36;44m Text \u001b[1;36;45m Text \u001b[1;36;46m Text \u001b[1;36;47m Text
\u001b[1;37;40m Text \u001b[1;37;41m Text \u001b[1;37;42m Text \u001b[1;37;43m Text \u001b[1;37;44m Text \u001b[1;37;45m Text \u001b[1;37;46m Text \u001b[1;37;47m Text
```
"""
        )

        _ =await interaction.response.send_message(embed=embed)


    @app_commands.command(
        name = 'pagination',
        description = 'Display paginated data with navigation buttons'
    )
    async def pagination(self, interaction: discord.Interaction):
        """Slash command to display paginated data"""

        await PaginatedView(
            interaction = interaction,
            total_pages = 4,
            get_page = get_pagination_embed
        ).setup()


    @app_commands.command(name = 'buttons',description = 'Display all possible button styles')
    @app_commands.describe(enabled = 'Weather the buttons are enabled or disabled')
    async def buttons(self, interaction: discord.Interaction, enabled:bool = True):
        """Slash command to display all possible discord embed button styles"""

        await ButtonsView(interaction=interaction, enabled=enabled).setup()


async def setup(bot: commands.Bot):  # pylint: disable=unused-argument
    """ Setup the Examples cog."""
    # Demonstration cog - intentionally not attached by default



### Paginaation Embed Generator ###


def  get_pagination_embed(index: int=0, embed: discord.Embed|None=None) -> discord.Embed:
    """ Returns a pagination embed with the respect data

        Parameters:
            index: index of the data block do be displayed
            embed: base embed to be modified
    """
    max_pages: int = len(example_data)
    index = max(0, min(index, max_pages-1)) # clamp to index to the range [0, max_pages)
    if embed is None:
        embed = discord.Embed(
            color = 0xaa92b4,
            title = 'Pagination - Example',
            description = 'A small Embed to display paginated data\n \u200B  '
        )
    _ =embed.set_author(
        name='Combifightet',
        url='https://github.com/combifightet',
        icon_url='https://avatars.githubusercontent.com/u/47188809'
    )
    _ = embed.add_field(
        name = f'Example ({index+1}/{max_pages})',
        value = example_data[index],
        inline = False
    )

    return embed

example_data:list[str] = [
    """
 \u200B
 0. Lorem ipsum dolor sit amet aliquyam autem lorem exerci aliquam lorem kasd lorem erat invidunt
     \u200B
    Gubergren        [**Euis.**](https://www.lipsum.com/)
     \u200B
    **Sadipscing**
   ```
   • Vel vero kasd erat et gubergren dolore
   • Eros et lorem eirmod at sit magna
   • Magna commodo kasd lorem eum
   • Eros erat consequat diam vero tempor ut labore erat et ea odio sed ea
   • Duo et dolore eum sed sea vulputate
   • Ut dolore illum clita lorem ipsum lorem rebum ut euism
   ```
 \u200B
 0. Vero invidunt et clita dolor at duis nonumy ut tempor est sanctus ipsum
     \u200B
    **Sadipscing**
   ```
   • Sadipscing gubergren et ea
   • Nonumy justo et exerci ipsum consetetur ullamcorper
   ```
""",
"""
 0. Justo kasd vel ea commodo sadipscing sed amet et
     \u200B
    **Sadipscing**
   ```
   • Diam aliquyam et quod elitr luptatum tempor sea diam
   • Voluptua dolor stet dolores amet
   • Ipsum ut justo duis kasd no sanctus diam
   • Praesent dolores et sed gubergren voluptua elitr
   ```
 \u200B
 0. Stet clita invidunt ut in volutpat lorem rebum eros accusam accusam erat dolor
     \u200B
    **Sadipscing**
   ```
   • Dolore ex stet eleifend est
   • Dolore et tempor accusam est sed sea
   ```
 \u200B
 0. Tation a       [**invidunt**](https://www.lipsum.com/)
     \u200B
    **Sadipscing**
   ```
   • Amet no et dolores in dolore stet
   ```
""",
"""
Est et dolor sanctus nonumy consetetur diam labore, ut facer duo volutpat sea accumsan accusam
 \u200B
Luptatum       **Feugait**
 \u200B
**Sadipscing**
```
• Zzril ipsum zzril dolore nisl
```
""",
"""
 0. Augue dolor option dolores et
     \u200B
    Luptatum       **Takimata**
 \u200B
 0. Luptatum       **ullamcortakimata**
     \u200B
    Tation a       [**Ullamcorper**](https://www.lipsum.com/)
"""
]


### Buttons View Class ###

class ButtonsView(discord.ui.View):
    """ Class for displaying each button type"""
    def __init__(self, interaction: discord.Interaction, enabled: bool = True):
        self.interaction: Interaction[Client] = interaction
        self.enabled: bool = enabled
        super().__init__(timeout=300)  # doesn't accept new interaction after <timeout> seconds

        link_button: Button[LayoutView] =     Button(
            emoji = '5️⃣',
            label = 'link / _url_',
            style = discord.ButtonStyle.link,
            url = 'https://github.com/combifightet',
            disabled=not self.enabled
        )
        _ = self.add_item(link_button)

        premium_button: Button[LayoutView] =     Button(
            style = discord.ButtonStyle.premium,
            sku_id = 1416080458093170820, # 'buy me a coffe'
            disabled = not self.enabled
        )
        _ = self.add_item(premium_button)

    @discord.ui.button(
            emoji='1️⃣',
            label='primary / _blurple_',
            style=discord.ButtonStyle.primary
        )
    async def primary(self, _interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Empty example callback"""

    @discord.ui.button(
            emoji='2️⃣',
            label='secondary / _grey_ /_gray_',
            style=discord.ButtonStyle.secondary)
    async def secondary(self, _interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Empty example callback"""

    @discord.ui.button(
            emoji='3️⃣',
            label='success / _green_',
            style=discord.ButtonStyle.success
        )
    async def success(self, _interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Empty example callback"""

    @discord.ui.button(
            emoji='4️⃣',
            label='danger / _red_',
            style=discord.ButtonStyle.danger
        )
    async def danger(self, _interaction: discord.Interaction, _button: Button[LayoutView]):
        """ Empty example callback"""

    async def setup(self):
        """ Setup button states and embed"""
        # Set the disabled state of all buttons after initialization
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = not self.enabled

        embed:discord.Embed = discord.Embed(
            colour=0xac91b4,
            title='Buttons - Example',
            description='A small Embed to display all 6 different button types',
        )
        _ = embed.set_author(
            name='Combifightet',
            url='https://github.com/combifightet',
            icon_url='https://avatars.githubusercontent.com/u/47188809'
        )
        _ = await self.interaction.response.send_message(embed=embed, view=self)



    @override
    async def on_timeout(self):
        # for item in self.children:
        #     item.disabled = True
        pass

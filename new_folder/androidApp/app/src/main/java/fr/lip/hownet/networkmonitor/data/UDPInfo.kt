package fr.lip.hownet.networkmonitor.data

data class UDPInfo(
    val ssid: String,
    val ipAddress: String,
    val port: Int,
    val message: String?
)

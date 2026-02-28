package fr.lip.hownet.networkmonitor.utils

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress


fun getMACAddress(context: Context, ssid: String): String {
    val TAG = "GetMACAddress"
    //val staticMacAddress = "2c:d0:66:3e:b3:02" // Replace with your desired static MAC address
    val staticMacAddress = "68:c4:4c:87:3c:94" // Replace with your desired static MAC address
    Log.d(TAG, "Returning static MAC address: $staticMacAddress")
    return staticMacAddress
}


fun sendUdpMessage(message: String, ipAddress: String, port: Int) {
    CoroutineScope(Dispatchers.IO).launch {
        try {
            val socket = DatagramSocket()
            val address: InetAddress = InetAddress.getByName(ipAddress)
            val packet = DatagramPacket(message.toByteArray(), message.length, address, port)
            socket.send(packet)
            socket.close()
            Log.d("NetworkUtils", "UDP sent: $message to $ipAddress:$port")
        } catch (e: Exception) {
            Log.e("NetworkUtils", "UDP send error: ${e.message}")
        }
    }
}
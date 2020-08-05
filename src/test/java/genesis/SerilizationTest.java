// Copyright (C) 2016 Fan Long, Peter Amidon, Martin Rianrd and MIT CSAIL 
// Genesis (A successor of Prophet for Java Programs)
// 
// This file is part of Genesis.
// 
// Genesis is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 2 of the License, or
// (at your option) any later version.
// 
// Genesis is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with Genesis.  If not, see <http://www.gnu.org/licenses/>.
package genesis;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.URL;

import junit.framework.TestCase;
import spoon.Launcher;
import org.junit.Test;

import genesis.node.MyCtNode;

/**
 * Unit test for Serilization of MyCtNode.
 */
public class SerilizationTest extends TestCase
{
    @Test
    public void test()
    {
        //assertTrue( true );
    	URL basicURL = getClass().getResource("/schema/basic/before1.jar");
    	TestSnippetParser parser = new TestSnippetParser(basicURL.getPath());
    	MyCtNode n = parser.getCtNode();
    	MyCtNode n1 = null;
    	//Launcher l = new Launcher();
    	try 
    	{
    		ObjectOutputStream os = new ObjectOutputStream(new FileOutputStream("/tmp/tmp.po"));
    		n.writeToStream(os);
    		os.close();
    		ObjectInputStream is = new ObjectInputStream(new FileInputStream("/tmp/tmp.po"));
    		n1 = MyCtNode.readFromStream(is);
    		is.close();
    	}
    	catch (Exception e) {
    		e.printStackTrace();
    		fail(e.getMessage());
    	}
    	assertTrue("Serilization gets inconsistent objects", n.treeEquals(n1));
    }
}
